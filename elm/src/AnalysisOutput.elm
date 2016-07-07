module AnalysisOutput exposing (..)

import Html exposing (..)
import Html.Attributes exposing (class, classList, attribute, type', name, rows, required, placeholder, value)
import Html.Events exposing (onClick)

import Array
import Date

import AnalysisOutputParameter
import ArrayComponent
import Raw
import Util


type alias Model =
    { id: Int
    , name: String
    , date_created: Date.Date
    , creator: String
    , analysis: String
    , output_parameters: Array.Array AnalysisOutputParameter.Model
    , files: Array.Array Raw.AnalysisOutputFile
    , showShareModal: Bool
    }


fromRawAnalysisOutput: Raw.AnalysisOutput -> Model
fromRawAnalysisOutput raw_analysisoutput =
    { id = raw_analysisoutput.id
    , name = raw_analysisoutput.name
    , date_created = raw_analysisoutput.date_created
    , creator = raw_analysisoutput.creator
    , analysis = raw_analysisoutput.analysis
    , output_parameters = raw_analysisoutput.parameter_values
    , files = raw_analysisoutput.files
    , showShareModal = False
    }


type Msg
    = ShowShareModal
    | CloseShareModal
    | ModifyOutputParameter Int AnalysisOutputParameter.Msg


update: Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        ShowShareModal -> Debug.log "ShowShareModal" ({ model | showShareModal = True }, Cmd.none)

        CloseShareModal -> Debug.log "CloseShareModal" ({ model | showShareModal = False }, Cmd.none)

        ModifyOutputParameter id paramter_msg -> Debug.crash "Bad"


viewOutputParameters: Model -> Html Msg
viewOutputParameters model =
    div []
        ((code [] [ text "Parameters"]) ::
        ArrayComponent.viewList ModifyOutputParameter AnalysisOutputParameter.view model.output_parameters)


view: Model -> Html Msg
view model =
    li [ class "list-group-item" ]
        [ h5 []
            [ span [ class "label label-primary" ]
                [ text model.creator ]
            , span [] [ text model.name ]
            , small [ class "pull-right"]
                [ span [ class "label labe-primary"]
                    [text (Util.dateToString model.date_created)]
                ]
            ]
        , div [ class "btn-group", attribute "role" "group" ]
            [ a [ class "btn btn-primary"]
                [ i [ class "fa fa-eye"] []
                , text " Details"
                ]
            , a [ class "btn btn-success", onClick ShowShareModal ]
                [ i [ class "fa fa-share"] []
                , text " Share"
                ]
            ]
        , div [ class "btn-group pull-right", attribute "role" "group" ]
            [ a [ class "btn btn-danger"]
                [ i [ class "fa fa-trash"] []
                , text " Delete"
                ]
            ]
        , viewShare model
        ]


viewShare: Model -> Html Msg
viewShare model =
    let modalClass =
            classList
                [ ("modal", True)
                , ("fade", True)
                , ("hidden", model.showShareModal)
                ]
    in
    div [ class "modal fade"]
        [ div [ class "modal-dialog model-lg"]
            [ div [ class "modal-header" ]
                [ button [ class "close", attribute "data-dismiss" "modal", attribute "aria-label" "Close"]
                    [ span [ class "fa fa-close", attribute "aria-hidden" "true"] [ ]
                    ]
                , h4 [ class "modal-title"]
                    [ text "Share an analysis run" ]
                ]
            , div [ class "modal-body"]
                [ div [ class "bs-callout bs-callout-info"]
                    [ h5 [] [ text model.name ]
                    , viewOutputParameters model
                    , code [] [ text "Output files:" ]
                    ]
                , form [ class "form form-horizontal" ]
                    [ input [ type' "hidden", name "id", value (toString model.id) ] []
                    , div [ class "form-group"]
                        [ div [ class "input-group"]
                            [ span [ class "input-group-addon"]
                                [ i [ class "fa fa-envelope"] [] ]
                            , input
                                [ type' "email"
                                , name "email"
                                , class "form-control"
                                , required True
                                , placeholder "Emails (use commas to separate multiple addresses)"
                                ] []
                            ]
                        ]
                    , div [ class "input-group" ]
                        [ div [ class "input-group" ]
                            [ span [ class "input-group-addon"]
                                [ i [ class "fa fa-paragraph"] [] ]
                            , textarea
                                [ class "form-control"
                                , name "message"
                                , rows 10
                                , required True
                                , placeholder "Enter your message here"
                                ] []
                            ]
                        ]
                    ]
                ]
            , div [ class "modal-footer" ]
                [ button
                    [ type' "button"
                    , class "btn btn-default"
                    , onClick CloseShareModal
                    ]

                    [ text "Cancel"
                    ]
                , button
                    [ type' "button"
                    , class "btn btn-primary"
                    , onClick CloseShareModal ]

                    [ i [ class "fa fa-share-alt"] []
                    , text "Share"
                    ]
                ]
            ]
        ]

