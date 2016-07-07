module Analysis exposing (..)

import Date

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.App as App

import Array

import AnalysisOutput
import ArrayComponent
import Parameter
import Raw
import Util


type alias Model =
    { id: Int
    , name: String
    , full_name: String
    , date_created: Date.Date
    , last_modified: Date.Date
    , description: String
    , project: String
    , file_type: String
    , parameters: Array.Array Parameter.Model
    , outputs: Array.Array AnalysisOutput.Model
    }


type Msg
    = ModifyParameter Int Parameter.Msg
    | ModifyOutput Int AnalysisOutput.Msg


fromRawAnalysis: Raw.Analysis -> Model
fromRawAnalysis raw_analysis =
    let parameters = Array.map Parameter.fromRawParameter raw_analysis.parameters
        outputs = Array.map AnalysisOutput.fromRawAnalysisOutput raw_analysis.outputs
    in { raw_analysis | parameters = parameters, outputs = outputs }


updateOutputs: Int -> AnalysisOutput.Msg -> Array.Array AnalysisOutput.Model -> (Array.Array AnalysisOutput.Model, Cmd Msg)
updateOutputs =
    ArrayComponent.updateChild ModifyOutput AnalysisOutput.update


update: Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        ModifyParameter id parameter_msg -> Debug.crash "ModifyParameter"

        ModifyOutput id output_msg ->
            let (outputs, msg') = updateOutputs id output_msg model
            in ({ model | outputs = outputs }, msg')


viewParameters model =
    ArrayComponent.viewList ModifyParameter Parameter.view model.parameters


viewOutputs model =
    ArrayComponent.viewList ModifyOutput AnalysisOutput.view model.outputs

viewAsWell model =
    div
        [ class "well" ]
        [ h5 []
            [ a []
                [ span [] [ text model.name ]
                , small [ class "pull-right" ]
                    [ span [ class "label label-primary" ]
                        [ text (Util.dateToString model.date_created) ]
                    ]
                ]
            ]
        , div []
            [ strong []
                [ text "Status " ]
            , mark []
                [ text "RUNNING" ]
            , i [ class "fa fa-spinner fa-pulse"]
                []
            ]
        , div []
            [ strong [] [ text "Description " ]
            , span []
                [ text model.description ]
            ]
        , div []
            [ strong [] [ text "Authors " ]
            , span [] [ text "No authors listed" ]
            ]
        , div []
            [ strong [] [ text "File Type "]
            , span [ class "label label-warning" ]
                [ text model.file_type ]
            ]
        , div []
            ((strong [] [ text "Parameters" ]) :: (viewParameters model))
        , div [ class "btn-group", attribute "role" "group" ]
            [ button [ class "btn btn-sm btn-default"]
                [ span [ class "fa fa-play"]
                    [ text "Run Script" ]
                ]
            , button [ class "btn btn-sm btn-default"]
                [ span [ class "fa fa-eye" ]
                    [ text "View Details" ]
                ]
            , button [ class "btn btn-sm btn-default" ]
                [ span [ class "fa fa-download" ]
                    [ text "Download" ]
                ]
            ]
        ]

viewOutputsAsWell model =
    ul [ class "list-group"]
        (viewOutputs model)