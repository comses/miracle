module Parameter exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)

import Array
import String

import Http
import Task

import Raw


type alias Model =
    { id: Int
    , name: String
    , label: String
    , data_type: String
    , description: String
    , value: String
    , html_input_type: String
    , allowed_values: String
    }


fromRawParameter: Raw.Parameter -> Model
fromRawParameter raw_parameter =
    let convertArr array = String.join "," (Array.toList array)
        allowed_values =
            case raw_parameter.value_list of
                Just x -> convertArr x
                Nothing ->
                    case raw_parameter.value_range of
                        Just x -> ("Range(" ++ (convertArr x) ++ ")")
                        Nothing -> "No allowed values"

    in
        { id = raw_parameter.id
        , name = raw_parameter.name
        , label = raw_parameter.label
        , data_type = raw_parameter.data_type
        , description = raw_parameter.description
        , value = raw_parameter.value
        , html_input_type = raw_parameter.html_input_type
        , allowed_values = allowed_values
        }


type Msg = NoOp


view: Model -> Html Msg
view model =
    let textColon val = text (": " ++ val)
        label =
            div []
                [ strong [] [ text model.label ]
                , i [] [ text ("(" ++ model.name ++ ")") ]
                ]
        data_type =
            div []
                [ strong [] [ text "Data Type" ]
                , span [] [ textColon model.data_type ]
                ]
        element_type =
            div []
                [ strong [] [ text "Element Type" ]
                , span [] [ textColon model.html_input_type ]
                ]
        allowed_values =
            div []
                [ strong [] [ text "Allowed Values" ]
                , span [] [ textColon model.allowed_values ]
                ]
        description =
            div []
                [ strong [] [ text "Description" ]
                , span [] [ textColon model.description ]
                ]
    in
    div [ class "alert alert-info alert-sm"]
        [ label
        , data_type
        , element_type
        , allowed_values
        , description
        ]