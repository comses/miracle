module TextField exposing (textfield, toString, update, view, Model, Msg(ToggleEditable,SetValue))

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onInput)

import Json.Decode as Decode exposing ((:=))
import DecodeExtra exposing (pure, apply)

type alias Model =
        { name: String
        , value: String
        , disabled: Bool
        }


toString: Model -> String
toString model = model.value


type Msg
        = SetValue String
        | ToggleEditable


view: Model -> Html Msg
view model =
    div []
        [ label [] [ text model.name ]
        , input
            [ type' "text"
            , disabled model.disabled
            , onInput SetValue
            , value model.value ] []]


update: Msg -> Model -> Model
update msg model =
    case msg of

        SetValue value -> { model | value = value }

        ToggleEditable -> { model | disabled = not model.disabled }


textfield: String -> String -> Model
textfield name value = { name = name, value = value, disabled = True }
