module Cancelable exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)

import Json.Decode as Decode exposing ((:=))
import DecodeExtra exposing (pure, apply)

type alias Model a =
        { current: a
        , old: a
        , dirty: Bool
        }


fromCancelable: Model a -> a
fromCancelable model = model.current


type Msg a
        = SetValue a
        | Dirty
        | Reset
        | Save


viewFormGroup:
    { tag: List (Attribute (Msg String)) -> List (Html (Msg String)) -> Html (Msg String)
    , attributes: List (Attribute (Msg String)) } ->
    Attribute (Msg String) ->
    Model String ->
    Html (Msg String) ->
    Html (Msg String)
viewFormGroup node onEventDirty model label_name =
    let textClass =
            classList
                [ ("form-group", True)
                , ("has-warning", model.dirty)
                ]
    in
    div [ onEventDirty, textClass ]
        [ label [ class "col-xs-2 control-label" ] [ label_name ]
        , div [ class "col-xs-10" ]
            [ node.tag ((class "form-control") :: node.attributes) []
            ]
        ]

viewTextField:
    Attribute (Msg String) ->
    Model String ->
    Html (Msg String) ->
    Html (Msg String)
viewTextField onEventDirty model =
    viewFormGroup
        { tag = input, attributes = [ type' "text", onInput SetValue, value model.current ]}
        onEventDirty
        model


viewTextArea:
    Attribute (Msg String) ->
    Model String ->
    Html (Msg String) ->
    Html (Msg String)
viewTextArea onEventDirty model =
    viewFormGroup
        { tag = textarea, attributes = [ onInput SetValue, value model.current ]}
        onEventDirty
        model



update: Msg a -> Model a -> Model a
update msg model =
    case msg of

        SetValue value -> { model | current = value }

        Dirty -> { model | dirty = True }

        Reset -> { model | current = model.old, dirty = False }

        Save -> { model | old = model.current }


toCancelable: a -> Model a
toCancelable value = { current = value, old = value, dirty = False }
