module DataColumn exposing (..)

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


viewTableRow: Model -> Html Msg
viewTableRow model =
    let text_name = text model.name
        td_full_name = App.map FullName (Cancelable.viewInputInTable model.full_name)
        td_data_type = App.map DataType (CancelableSelect.viewSelectInTable model.data_type)
        td_description = App.map Description (Cancelable.viewTextAreaInTable model.description)
    in
    tr
        [ ]
        [ td
            [ ]
            [ h6
                [ ]
                [ text_name ]
            ]
        , td_full_name
        , td_data_type
        , td_description
        , td
            [ ]
            [ div
                [ class "btn-group btn-group-sm pull-right"]
                [ button
                    [ onClick Set, class "btn btn-primary" ]
                    [ span [ class "fa fa-floppy-o", attribute "aria-hidden" "true" ] [] ]
                , button
                    [ onClick Reset, class "btn btn-primary" ]
                    [ span [ class "fa fa-undo", attribute "aria-hidden" "true" ] [] ]
                ]
            ]
        ]


set: Model -> Cmd Msg
set model =
    Task.perform
        (toString >> FetchFail)
        FetchSucceed
        (Api.DataColumn.setTask (Debug.log "Column" (toColumn model)) |> (Http.fromJson Raw.columnDecoder))

