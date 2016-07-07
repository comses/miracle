module AnalysisTab exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.App as App

import Array
import Json.Decode

import Analysis
import ArrayComponent
import Project
import Raw
import Util

type alias Model = Project.Model


type alias Msg = Project.Msg


viewAnalyses: Model -> List (Html Msg)
viewAnalyses model =
    ArrayComponent.viewList Project.ModifyAnalysis Analysis.viewAsWell model.analyses


viewAnalysisOutputs: Model -> List (Html Msg)
viewAnalysisOutputs model =
    ArrayComponent.viewList Project.ModifyAnalysis Analysis.viewOutputsAsWell model.analyses


view: Model -> Html Msg
view model =
    div [ class "row" ]
        [ Util.displayInPanel 6 "Data Analysis Scripts" (viewAnalyses model)
        , Util.displayInPanel 6 "Analysis Outputs" (viewAnalysisOutputs model)
        ]


main = App.programWithFlags
    { init = Project.init
    , update = Project.update
    , subscriptions = \_ -> Sub.none
    , view = view
    }