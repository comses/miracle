module Metadata exposing (update, view, init)

import Html exposing (..)
import Html.App as App
import Html.Attributes exposing (class, type', value)
import Html.Events exposing (onClick)
import Http
import Task
import Debug
import Json.Encode as Encode
import Platform.Cmd

import Api.DataTableGroup
import Api.DataColumn

import Csrf

import DataColumn as Column
import DataTableGroup

import Raw

type alias Model =
    { datatablegroup: DataTableGroup.Model
    , warning: String
    , loading: Bool
    }


type Msg
    = Content DataTableGroup.Msg
    | Reset
    | DataTableGroupR Api.DataTableGroup.Msg
    | DataColumnR Int Api.DataColumn.Msg


updateDataTableGroupR: Api.DataTableGroup.Msg -> Model -> (Model, Cmd Msg)
updateDataTableGroupR msg model =
    let mapDTG = Platform.Cmd.map DataTableGroupR
    in case msg of

        Api.DataTableGroup.Get id -> (model, mapDTG (Api.DataTableGroup.get id))

        Api.DataTableGroup.Set ->

            let _ = Debug.log "CSRFToken: " Csrf.getCsrfToken
                _ = Debug.log "Current: " model.datatablegroup
                datatablegroup = DataTableGroup.toDataTableGroup model.datatablegroup
                _ = Debug.log "Set: " datatablegroup

            in (model, mapDTG (Api.DataTableGroup.set model.datatablegroup))

        Api.DataTableGroup.FetchFail error ->
            ({ model | warning = toString error }, Cmd.none)

        Api.DataTableGroup.FetchSucceed raw_datatablegroup ->

            let _ = Debug.log "FetchSucceeded" raw_datatablegroup
                datatablegroup = DataTableGroup.fromDataTableGroup raw_datatablegroup

            in ({model | datatablegroup = datatablegroup
                       , loading = False}, Cmd.none)


-- TODO: make a updateDataColumnR function to deal with
--updateDataColumnR: Api.DataColumn.Msg -> Api.Model -> (Api.Model, Cmd Api.Msg)
--updateDataColumnR msg model =
--    case msg of
--
--        Api.DataColumn.Set id -> (model, Api.setDataColumnCmd id)


update: Msg -> Model -> (Model, Cmd Msg)
update msg model = 
    case msg of
        Content msg' ->
            ({ model | datatablegroup = DataTableGroup.update msg' model.datatablegroup }, Cmd.none)

        Reset -> ({ model | warning = ""
                              , datatablegroup = DataTableGroup.update DataTableGroup.Reset model.datatablegroup}
                     , Cmd.none)

        DataTableGroupR msg' -> updateDataTableGroupR msg' model

        DataColumnR id msg' -> (model, Cmd.none)


view: Model -> Html Msg
view model =
    let onClickDtgBtn = onClick (DataTableGroupR Api.DataTableGroup.Set)

        contents = if model.loading then [ text "Loading" ]
            else [ h4 [] [ text "Metadata" ]
            , App.map Content (DataTableGroup.view model.datatablegroup)
            , input [ type' "button", onClickDtgBtn, class "btn", value "Save"] []
            , input [ type' "button", onClick Reset, class "btn", value "Cancel"] []
            ]

        contents_with_warning = if model.warning /= "" then
            contents ++ [ text model.warning ]
            else contents
    in

    div [ class "container"] contents_with_warning


init: {id: Int} -> (Model, Cmd Msg)
init {id} =
    let mapDTG = Platform.Cmd.map DataTableGroupR
        model =
            { datatablegroup= DataTableGroup.init
            , warning=""
            , loading=True
            }
    in (model, mapDTG (Api.DataTableGroup.get id))


main = App.programWithFlags { init = init, view = view, update = update, subscriptions = \_ -> Sub.none }