module StyledNodes exposing (..)

import Html as H
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Json.Decode as Decode


onChange : msg -> H.Attribute msg
onChange message =
    on "change" (Decode.succeed message)

onChangeIndex : (Int -> msg) -> H.Attribute msg
onChangeIndex tagger =
    let value = Decode.at ["target", "selectedIndex"] Decode.int
    in on "change" (Decode.map tagger value)

button_submit = [ ("btn", True), ("btn-primary", True) ]
button_cancel = [ ("btn", True), ("btn-default", True) ]