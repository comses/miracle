module CancelableSelect exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.App as App

import Array

import Cancelable
import Util

import Debug

type alias Model =
    { options: Array.Array (String, String)
    , currentSelectedIndex: Maybe Int
    , oldSelectedIndex: Maybe Int
    , dirty: Bool
    }


type Msg
    = Select Int
    | Dirty
    | Reset
    | Save


update: Msg -> Model -> Model
update msg model =
    case msg of

        Select index -> { model | currentSelectedIndex = Just index }

        Dirty -> { model | dirty = True }

        Reset -> { model | currentSelectedIndex = model.oldSelectedIndex, dirty = False }

        Save -> { model | oldSelectedIndex = model.currentSelectedIndex }


viewSelectInTable: Model -> Html Msg
viewSelectInTable model =
    let tdClass = classList
            [ ("metadata-td", True)
            , ("has-warning", model.dirty)
            ]
        options = List.map
            (\(id, (val, name)) -> option [ value val, selected (model.currentSelectedIndex == Just id) ] [ text name ])
            (Array.toIndexedList model.options)
    in
        td [ Util.onChange Dirty, tdClass ]
            [ select
                [ Util.onChangeIndex Select, class "form-control" ]
                options
            ]


index: String -> Array.Array String -> Maybe Int
index value' values =
    let (ind, max_ind) =
            Array.foldl
                (\value (cur_val, ind) ->
                    case cur_val of
                        Just _ -> (cur_val, ind+1)

                        Nothing -> if value' == value then (Just ind, ind+1) else (Nothing, ind+1))
                    (Nothing, 0)
                values
    in ind


toCancelableSelect: String -> Model
toCancelableSelect value =
    let options =
            Array.fromList
                [ ("decimal", "floating point number")
                , ("boolean", "boolean")
                , ("bigint", "integer")
                , ("text", "text")
                , ("date", "date")
                ]
        selectedIndex = index value
            (Array.map (\(val, text) -> val ) options)
    in
    { options = options
    , currentSelectedIndex = selectedIndex
    , oldSelectedIndex = selectedIndex
    , dirty = False
    }


fromCancelableSelect: Model -> String
fromCancelableSelect model =
    model.currentSelectedIndex
        `Maybe.andThen` (\i -> Array.get i model.options)
        `Maybe.andThen` (\(val, text) -> Just val) |> Maybe.withDefault ""
