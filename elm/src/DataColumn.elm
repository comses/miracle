module DataColumn exposing (column, Model, Msg, update, view)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.App as App
import Html.Events exposing (onBlur, onClick, onInput)
import TextField exposing (textfield)
import Json.Decode as Decode exposing ((:=))
import DecodeExtra exposing (apply, pure)
import Json.Encode as Encode


type alias Model =
    { id: Int
    , name: String
    , full_name: TextField.Model
    , description: TextField.Model
    , warning: String
    }


columnDecode: Decode.Decoder Model
columnDecode =
    pure Model
    `apply` ("id":= Decode.int)
    `apply` ("name":= Decode.string)
    `apply` ("full_name":= Decode.string)
    `apply` ("description":= Decode.string)


type Msg 
    = Name String
    | FullName TextField.Msg
    | Description TextField.Msg
    | Edit
    | Warn String


column: { id: Int, name: String, full_name: String, description: String } -> Model
column {id, name, full_name, description} =
    { id = id
    , name = name
    , full_name = textfield "Full Name" full_name
    , description = textfield "Description" description
    , warning = ""
    }


init: Model
init = column 
    { id=1
    , name="price_data"
    , full_name="Price Data"
    , description="Purchase price of a home"
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
