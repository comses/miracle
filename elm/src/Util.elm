module Util exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Json.Decode as Decode
import Date
import Date.Format


onChange : msg -> Attribute msg
onChange message =
    on "change" (Decode.succeed message)


onChangeIndex : (Int -> msg) -> Attribute msg
onChangeIndex tagger =
    let value = Decode.at ["target", "selectedIndex"] Decode.int
    in on "change" (Decode.map tagger value)


displayInPanel: Int -> String -> List (Html msg) -> Html msg
displayInPanel width name view =
    div [ class ("col-lg-" ++ toString width) ]
        [ div [ class "panel panel-primary" ]
            [ div [ class "panel-heading" ]
                [ text name ]
                , div [ class "panel-body" ]
                    view
                ]
            ]


dateToString: Date.Date -> String
dateToString = Date.Format.formatISO8601