module MetadataTab exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onClick)
import Html.App as App

import Array
import Json.Decode

import Cancelable
import DataTableGroup
import Project
import Raw

type alias Model = Project.Model
type alias Msg = Project.Msg


view: Model -> Html Msg
view model =
    let indexed_model = Array.toIndexedList model.data_table_groups
        viewColumnForms = List.map viewDataTableGroupColumns indexed_model
        viewForms = List.map viewDataTableGroup indexed_model
        displayInPanel width name view =
            div [ class ("col-lg-" ++ toString width) ]
                [ div [ class "panel panel-primary" ]
                    [ div [ class "panel-heading" ]
                        [ text name ]
                        , div [ class "panel-body" ]
                            view
                        ]
                    ]
        contents =
            [ div [ class "row" ]
                [ displayInPanel 4 "Data Table Groups" viewForms
                , displayInPanel 8 "Data Table Group Columns" viewColumnForms
                ]
            ]


        contents_with_warning = if model.warning /= "" then
            contents ++ [ text model.warning ]
            else contents
    in

    div [ class "container-fluid"] contents_with_warning


viewDataTableGroupColumns: (Int, DataTableGroup.Model) -> Html Msg
viewDataTableGroupColumns (id, model) = App.map (Project.ModifyDataTableGroup id)
    (DataTableGroup.view (DataTableGroup.viewTableRows model) model)


viewDataTableGroup: (Int, DataTableGroup.Model) -> Html Msg
viewDataTableGroup (id, model) = App.map (Project.ModifyDataTableGroup id)
    (DataTableGroup.view (DataTableGroup.viewForm model) model)


main = App.programWithFlags
    { init = Project.init
    , update = Project.update
    , subscriptions = \_ -> Sub.none
    , view = view
    }