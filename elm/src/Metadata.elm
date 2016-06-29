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

import Array

import Api.DataTableGroup
import Api.DataColumn

import Csrf

import DataColumn as Column
import DataTableGroup

import Raw

type alias Model = Array.Array DataTableGroup.Model

type Msg
    = Modify Int DataTableGroup.Msg


update: Msg -> Model -> (Model, Cmd Msg)
update msg model = 
    case msg of
        Modify id datatablegroup_msg ->
            let datatablegroup = Array.get id model
                val = Maybe.map (DataTableGroup.update datatablegroup_msg) datatablegroup
            in case val of

                Just (datatablegroup', datatablegroup_msg') ->
                    (Array.set id datatablegroup' model, Cmd.map (Modify id) datatablegroup_msg')

                Nothing ->
                    (model, Cmd.none)



view: Model -> Html Msg
view model =
    let contents =
            [ h4 [] [ text "Metadata" ]
            , List.map viewDataTableGroup (Array.toIndexedList model)
            ]

        contents_with_warning = if model.warning /= "" then
            contents ++ [ text model.warning ]
            else contents
    in

    div [ class "container"] contents_with_warning


viewDataTableGroup: (Int, DataTableGroup.Model) -> Html Msg
viewDataTableGroup (id, model) = App.map (Modify id) (DataTableGroup.view model)


init: {id: Int} -> (Model, Cmd Msg)
init {id} =
    let (datatablegroup, datatablegroup_cmd) = DataTableGroup.init {id = id}
        model = datatablegroup
    in (model, Cmd.map (Modify id) datatablegroup_cmd)


main = App.programWithFlags { init = init, view = view, update = update, subscriptions = \_ -> Sub.none }