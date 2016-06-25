module DataColumn exposing (fromColumn, toColumn, Model, Msg, update, view)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.App as App
import Html.Events exposing (onBlur, onClick, onInput)
import Cancelable exposing (fromCancelable, toCancelable)

import StyledNodes as SN
import Csrf
import Json.Encode as Encode
import Raw as R


type alias Model =
    { id: Int
    , name: String
    , full_name: Cancelable.Model String
    , description: Cancelable.Model String
    , data_table_group: String
    , data_type: Cancelable.Model String
    , table_order: Int
    , warning: String
    , dirty: Bool
    }


type Msg 
    = Name String
    | FullName (Cancelable.Msg String)
    | Description (Cancelable.Msg String)
    | Warn String
    | Reset
    | Dirty
    | Update Model


fromColumn: R.Column -> Model
fromColumn {id, name, full_name, description, data_table_group, data_type, table_order} =
    { id = id
    , name = name
    , full_name = toCancelable full_name
    , description = toCancelable description
    , data_table_group = data_table_group
    , data_type = toCancelable data_type
    , table_order = table_order
    , warning = ""
    , dirty = False
    }


toColumn: Model -> R.Column
toColumn {id, name, full_name, description, data_table_group, data_type, table_order, warning, dirty} =
    { id = id
    , name = name
    , full_name = fromCancelable full_name
    , description = fromCancelable description
    , data_table_group = data_table_group
    , data_type = fromCancelable data_type
    , table_order = table_order
    }


update: Msg -> Model -> Model
update msg model =
    case msg of
        Name name -> { model | name = name }
    
        FullName msg -> { model | full_name = Cancelable.update msg model.full_name }

        Description msg -> { model | description = Cancelable.update msg model.description }

        Warn warning -> { model | warning = warning }

        Reset -> { model | dirty = False
                         , full_name = Cancelable.update Cancelable.Reset model.full_name
                         , description = Cancelable.update Cancelable.Reset model.description
                         , warning = "" }

        Dirty -> { model | dirty = True }

        Update model' -> model'


view: Model -> Html Msg
view model = 
    let view_name = h5 [] [ text model.name ]
        view_full_name = App.map FullName (Cancelable.viewTextField model.full_name "Full Name")
        view_description = App.map Description (Cancelable.viewTextField model.description "Description")

        btnClass = classList
            [ ("btn", True)
            , ("btn-primary", True)
            , ("hidden", not model.dirty)
            ]
        divClass = classList
            [ ("form-group", True)
            , ("has-warning", model.dirty)
            ]

    in div
        [ ]

        [ div
            [ SN.onChange Dirty
            , divClass
            ]

            [ view_name
            , view_full_name
            , view_description
            ]
        , input [ type' "button", btnClass, value "Save"] []
        , input [ type' "button", onClick Reset, btnClass, value "Cancel" ] []
        ]

