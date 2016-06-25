module Cancelable exposing (toCancelable, fromCancelable, update, viewTextField, Model, Msg(..))

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)

import Json.Decode as Decode exposing ((:=))
import DecodeExtra exposing (pure, apply)
import StyledNodes as SN

type alias Model a =
        { current: a
        , old: a
        }


fromCancelable: Model a -> a
fromCancelable model = model.current


type Msg a
        = SetValue a
        | Reset
        | Save


viewTextField: Model String -> String -> Html (Msg String)
viewTextField model name =
    div []
        [ label [] [ text name ]
        , input
            [ type' "text"
            , classList
                [ ("form-control", True) ]
            , onInput SetValue
            , value model.current ] []
        ]


update: Msg a -> Model a -> Model a
update msg model =
    case msg of

        SetValue value -> { model | current = value }

        Reset -> { model | current = model.old }

        Save -> { model | old = model.current }


toCancelable: a -> Model a
toCancelable value = { current = value, old = value }
