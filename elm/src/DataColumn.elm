module DataColumn exposing (fromColumn, toColumn, Model, Msg, update, view)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.App as App
import Html.Events exposing (onBlur, onClick, onInput)
import TextField exposing (textfield)
import Json.Decode as Decode exposing ((:=))
import DecodeExtra exposing (apply, pure)
import Json.Encode as Encode

import Raw exposing (Column)

type alias Model =
    { id: Int
    , name: String
    , full_name: TextField.Model
    , description: TextField.Model
    , data_table_group: String
    , data_type: String
    , table_order: Int
    , warning: String
    }


type Msg 
    = Name String
    | FullName TextField.Msg
    | Description TextField.Msg
    | Edit
    | Warn String


fromColumn: Column -> Model
fromColumn {id, name, full_name, description, data_table_group, data_type, table_order} =
    { id = id
    , name = name
    , full_name = textfield "Full Name" full_name
    , description = textfield "Description" description
    , data_table_group = data_table_group
    , data_type = data_type
    , table_order = table_order
    , warning = ""
    }


toColumn: Model -> Column
toColumn {id, name, full_name, description, data_table_group, data_type, table_order, warning} =
    { id = id
    , name = name
    , full_name = TextField.toString full_name
    , description = TextField.toString description
    , data_table_group = data_table_group
    , data_type = data_type
    , table_order = table_order
    }


update: Msg -> Model -> Model
update msg model =
    case msg of
        Name name -> { model | name = name }
    
        FullName msg -> { model | full_name = TextField.update msg model.full_name }

        Description msg -> { model | description = TextField.update msg model.description }

        Warn warning -> { model | warning = warning }

        Edit ->  { model
                 | full_name = TextField.update TextField.ToggleEditable model.full_name
                 , description = TextField.update TextField.ToggleEditable model.description }


view: Model -> Html Msg
view model = 
    let view_name = h2 [] [ text model.name ]
        view_full_name = App.map FullName (TextField.view model.full_name)
        view_description = App.map Description (TextField.view model.description)
    in div [ class "row" ] 
        [ view_name
        , view_full_name
        , view_description
        , input [ type' "button", onClick Edit, value "Edit" ] []]
