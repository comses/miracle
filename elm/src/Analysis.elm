module Analysis exposing (..)

import Date

import Html exposing (Html, button, div, text)
import Html.App as App

import Raw


type alias Model = Raw.Analysis


fromRawAnalysis: Raw.Analysis -> Model
fromRawAnalysis = identity


toRawAnalysis: Model -> Raw.Analysis
toRawAnalysis = identity