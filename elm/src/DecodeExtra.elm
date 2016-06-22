module DecodeExtra exposing (pure, apply)

import Json.Decode exposing (..)

pure: a -> Decoder a
pure = succeed


apply: Decoder (a -> b) -> Decoder a -> Decoder b
apply = object2 (<|)
