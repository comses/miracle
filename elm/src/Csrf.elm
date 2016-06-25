module Csrf exposing (..)

import Native.Csrf

addOne: Int -> Int
addOne = Native.Csrf.addOne

getCsrfToken: String
getCsrfToken = Maybe.withDefault "" Native.Csrf.getCsrfToken