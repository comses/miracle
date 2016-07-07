module AnalysisOutputParameter exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)

import Array

import ArrayComponent
import Raw


type alias Model = Raw.AnalysisOutputParameter


type Msg = NoOp


update: Msg -> Model -> (Model, Cmd Msg)
update msg model = (model, Cmd.none)


view: Model -> Html Msg
view model =
    li [ class "list-group-item" ]
        [ span [] [ text model.label ]
        , text "("
        , mark [] [ text model.value ]
        , text ")"
        ]