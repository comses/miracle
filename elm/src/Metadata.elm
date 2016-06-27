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

type alias Model = DataTableGroup.Model

type Msg
    = Content DataTableGroup.Msg


update: Msg -> Model -> (Model, Cmd Msg)
update msg model = 
    case msg of
        Content datatablegroup_msg ->
            let (datatablegroup', datatablegroup_msg') = DataTableGroup.update datatablegroup_msg model
            in (datatablegroup', Cmd.map Content datatablegroup_msg')


view: Model -> Html Msg
view model =
    let contents =
            [ h4 [] [ text "Metadata" ]
            , App.map Content (DataTableGroup.view model)
            ]

        contents_with_warning = if model.warning /= "" then
            contents ++ [ text model.warning ]
            else contents
    in

    div [ class "container"] contents_with_warning


init: {id: Int} -> (Model, Cmd Msg)
init {id} =
    let (datatablegroup, datatablegroup_cmd) = DataTableGroup.init {id = id}
        model = datatablegroup
    in (model, Cmd.map Content datatablegroup_cmd)


main = App.programWithFlags { init = init, view = view, update = update, subscriptions = \_ -> Sub.none }