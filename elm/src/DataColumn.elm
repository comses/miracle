module DataColumn exposing (fromColumn, toColumn, Model, Msg, update, view)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.App as App
import Html.Events exposing (onBlur, onClick, onInput)

import Http
import Task

import Api.DataColumn

import Cancelable exposing (fromCancelable, toCancelable)
import CancelableSelect exposing (fromCancelableSelect, toCancelableSelect)
import Util
import Csrf
import Json.Encode as Encode
import Raw


type alias Model =
    { id: Int
    , name: String
    , full_name: Cancelable.Model String
    , description: Cancelable.Model String
    , data_table_group: String
    , data_type: CancelableSelect.Model
    , table_order: Int
    , warning: String
    , dirty: Bool
    , expanded: Bool
    }


type Msg 
    = Name String
    | FullName (Cancelable.Msg String)
    | Description (Cancelable.Msg String)
    | DataType (CancelableSelect.Msg)
    | Warn String
    | Reset
    | Dirty
    | Expand
    | Update Model
    | Set
    | FetchSucceed Raw.Column
    | FetchFail String


fromColumn: Raw.Column -> Model
fromColumn {id, name, full_name, description, data_table_group, data_type, table_order} =
    { id = id
    , name = name
    , full_name = toCancelable full_name
    , description = toCancelable description
    , data_table_group = data_table_group
    , data_type = toCancelableSelect data_type
    , table_order = table_order
    , warning = ""
    , dirty = False
    , expanded = False
    }


toColumn: Model -> Raw.Column
toColumn {id, name, full_name, description, data_table_group, data_type, table_order, warning, dirty} =
    { id = id
    , name = name
    , full_name = fromCancelable full_name
    , description = fromCancelable description
    , data_table_group = data_table_group
    , data_type = fromCancelableSelect data_type
    , table_order = table_order
    }


update: Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        Name name -> ({ model | name = name }, Cmd.none)
    
        FullName msg' -> ({ model | full_name = Cancelable.update msg' model.full_name }, Cmd.none)

        Description msg' -> ({ model | description = Cancelable.update msg' model.description }, Cmd.none)

        DataType msg' -> ({ model | data_type = CancelableSelect.update msg' model.data_type }, Cmd.none)

        Warn warning -> ({ model | warning = warning }, Cmd.none)

        Reset -> ({ model | dirty = False
                          , full_name = Cancelable.update Cancelable.Reset model.full_name
                          , description = Cancelable.update Cancelable.Reset model.description
                          , data_type = CancelableSelect.update CancelableSelect.Reset model.data_type
                          , warning = "" }, Cmd.none)

        Dirty -> ({ model | dirty = True }, Cmd.none)

        Expand -> ({ model | expanded = not model.expanded }, Cmd.none)

        Update model' -> (model', Cmd.none)

        Set -> (model, set model)

        FetchSucceed raw_column -> (fromColumn raw_column, Cmd.none)

        FetchFail error -> ({ model | warning = error }, Cmd.none)


lessPadding = style
    [ ("padding", "5px 5px")]

view: Model -> Html Msg
view model = 
    let view_full_name =
            App.map FullName
                (Cancelable.viewTextField
                    (Util.onChange Cancelable.Dirty)
                    model.full_name
                    (text "Full Name"))
        view_description =
            App.map Description
                (Cancelable.viewTextArea
                    (Util.onChange Cancelable.Dirty)
                    model.description
                    (text "Description"))
        view_data_type = App.map DataType (CancelableSelect.view [] (text "Data Type") model.data_type)

        btnClass = class "btn btn-primary"
        view_title_class = classList
            [ ("text-primary", model.expanded)]
        view_head_full_name = text (Cancelable.fromCancelable model.full_name)
        view_head_name = text model.name

        form_body =
            if model.expanded then
                [ br [] []
                , div
                    [ Util.onChange Dirty
                    , class "form form-horizontal"
                    ]

                    [ view_full_name
                    , view_description
                    , view_data_type
                    , div [ class "form-group" ]
                        [ div [ class "btn-group col-xs-offset-2" ]
                            [ button [ onClick Set, btnClass ] [ text "Save" ]
                            , button [ onClick Reset, btnClass ] [ text "Cancel" ]
                            ]
                        ]
                    ]
                ]
            else []

--style [ ("overflow-y", "auto"), ("padding", "5px 5px") ]
    in
        li  [ class "item-metadata list-group-item" ]
            ([ div
                [ onClick Expand
                , classList
                    [ ("item-metadata-header", True)
                    , ("item-metadata-header-selected", model.expanded)
                    ]
                ]

                [ div [ class "pull-left" ]
                    [ view_head_name ]
                , div [ class "pull-right" ]
                    [ view_head_full_name ]
                ]

            ] ++ form_body)



set: Model -> Cmd Msg
set model =
    Task.perform
        (toString >> FetchFail)
        FetchSucceed
        (Api.DataColumn.setTask (Debug.log "Column" (toColumn model)) |> (Http.fromJson Raw.columnDecoder))

