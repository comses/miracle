module ArrayComponent exposing (..)

import Html exposing (..)
import Html.App as App

import Array


type alias Model submodel = Array.Array submodel


type alias Update msg model = msg -> model -> (model, Cmd msg)
type alias View msg model = model -> Html msg
type alias Modify submsg msg = Int -> submsg -> msg


updateChild: Modify submsg msg -> Update submsg submodel -> Int -> submsg -> Array.Array submodel -> (Array.Array submodel, Cmd msg)
updateChild modify subupdate id submsg model =
    let val = Array.get id model
    in
        case val of
            Just submodel ->
                let (item', cmd_submsg) = subupdate submsg submodel
                in
                    ( Array.set id item' model
                    , Cmd.map (modify id) cmd_submsg
                    )

            Nothing -> (model, Cmd.none)


viewList: Modify submsg msg -> View submsg submodel -> Array.Array submodel -> List (Html msg)
viewList modify subview model =
    let indexed_model = Array.toIndexedList model
        mkView (id, item) = App.map (modify id) (subview item)
        views = List.map mkView indexed_model
    in
        views