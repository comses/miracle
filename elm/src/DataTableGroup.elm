module DataTableGroup exposing (Model, Msg, update, view, init)

import Html exposing (..)
import Html.App as App
import Html.Attributes exposing (type', value)
import Html.Events exposing (onClick)

import Platform.Cmd as Cmd

import IntDict

import DataColumn as Column exposing (column)
import TextField exposing (textfield)
import Raw exposing (DataTableGroup)

type alias Model = 
    { id: Int
    , name: String 
    , full_name: TextField.Model 
    , description: TextField.Model
    , indexed_columns: IntDict.IntDict Column.Model
    , warning: String
    }


type Msg 
    = FullName TextField.Msg
    | Description TextField.Msg
    | Modify Int Column.Msg 
    | Edit


init: Model
init =
    { id=0
    , name="price_data"
    , full_name=textfield "Full Name" "Price Data"
    , description=textfield "Description" "Foo"
    , indexed_columns=IntDict.fromList [
        (0
        , column 
            { id = 0
            , name= "price"
            , full_name= "Price (2003 USD)"
            , description= "Purchase price of home in 2003 USD"
            }
        ),
        (1
        , column
            { id=1
            , name="n_of_agents"
            , full_name="Number of Agents"
            , description=""
            }
        )]
    , warning=""
    }


update: Msg -> Model -> Model
update msg model =
    case msg of
        FullName msg -> { model | full_name = TextField.update msg model.full_name }

        Description msg -> { model | description = TextField.update msg model.description }

        Modify id col_msg ->
            let column = IntDict.get id model.indexed_columns
                val =  Maybe.map (Column.update col_msg) column
            in case val of

                Just column' ->
                        { model | indexed_columns 
                                = IntDict.update id (always (Just column')) model.indexed_columns }

                Nothing -> model

        Edit -> { model
                | full_name = TextField.update TextField.ToggleEditable model.full_name
                , description = TextField.update TextField.ToggleEditable model.description }


view: Model -> Html Msg
view model =
    div []
        [ h1 [] 
            [ text "DataGroup: "
            , viewTextField model.full_name
            , input [ type' "button", onClick Edit, value "Edit" ] []
            , i [] [text (" " ++ model.name) ]]
        , div [] (List.map viewColumn (IntDict.toList model.indexed_columns))
        ] 



viewTextField: TextField.Model -> Html Msg
viewTextField model = App.map FullName (TextField.view model)


viewColumn: (Int, Column.Model) -> Html Msg
viewColumn (id, model) =
    App.map (Modify id) (Column.view model)


main = App.beginnerProgram { update = update, view = view, model = init }
