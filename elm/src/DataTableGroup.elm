module DataTableGroup exposing (Model, toDataTableGroup, fromDataTableGroup, rawStr, Msg, update, view, init)

import Html exposing (..)
import Html.App as App
import Html.Attributes exposing (type', value)
import Html.Events exposing (onClick)

import Platform.Cmd as Cmd

import IntDict
import Array

import DataColumn as Column exposing (column)
import TextField exposing (textfield)
import Raw exposing (DataTableGroup, columnEx)


type alias Model = 
    { id: Int
    , name: String 
    , full_name: TextField.Model 
    , description: TextField.Model
    , project: String
    , url: String
    , number_of_files: Int
    , number_of_columns: Int
    , indexed_columns: IntDict.IntDict Column.Model
    }


toDataTableGroup: Model -> DataTableGroup
toDataTableGroup model =
    { id=model.id
    , name=model.name
    , full_name= TextField.toString model.full_name
    , description= TextField.toString model.description
    , project= model.project
    , url= model.url
    , number_of_files= model.number_of_files
    , number_of_columns= model.number_of_columns
    , columns =
        Array.fromList (List.map Column.fromColumn (IntDict.values model.indexed_columns))
    }


fromDataTableGroup: DataTableGroup -> Model
fromDataTableGroup datatablegroup =
    { id= datatablegroup.id
    , name= datatablegroup.name
    , full_name= textfield "Full Name" datatablegroup.full_name
    , description= textfield "Description" datatablegroup.description
    , project= datatablegroup.project
    , url = datatablegroup.url
    , number_of_files= datatablegroup.number_of_files
    , number_of_columns = datatablegroup.number_of_columns
    , indexed_columns = IntDict.fromList  (Array.toIndexedList (Array.map Column.column datatablegroup.columns))
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
    , project="Luxe Demo"
    , url="/data-groups/1/"
    , number_of_files= 10
    , number_of_columns= 20
    , indexed_columns=IntDict.fromList [
        (0
        , column columnEx
        ),
        (1
        , column { columnEx | id = 1}
        )]
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


rawStr = """{"id":1,"name":"runLog","full_name":"","description":"","project":"luxedemo","url":"https://localhost/data-group/1.json","columns":[{"id":1,"data_table_group":"runLog","name":"runID","full_name":"","description":"","data_type":"bigint","table_order":1},{"id":2,"data_table_group":"runLog","name":"random","full_name":"","description":"","data_type":"bigint","table_order":2},{"id":3,"data_table_group":"runLog","name":"runNumber","full_name":"","description":"","data_type":"bigint","table_order":3},{"id":4,"data_table_group":"runLog","name":"msgOutLevel","full_name":"","description":"","data_type":"bigint","table_order":4},{"id":5,"data_table_group":"runLog","name":"worldx","full_name":"","description":"","data_type":"bigint","table_order":5},{"id":6,"data_table_group":"runLog","name":"worldy","full_name":"","description":"","data_type":"bigint","table_order":6},{"id":7,"data_table_group":"runLog","name":"centerx","full_name":"","description":"","data_type":"bigint","table_order":7},{"id":8,"data_table_group":"runLog","name":"centery","full_name":"","description":"","data_type":"bigint","table_order":8},{"id":9,"data_table_group":"runLog","name":"buyer","full_name":"","description":"","data_type":"bigint","table_order":9},{"id":10,"data_table_group":"runLog","name":"seller","full_name":"","description":"","data_type":"bigint","table_order":10},{"id":11,"data_table_group":"runLog","name":"maxBiddingTries","full_name":"","description":"","data_type":"bigint","table_order":11},{"id":12,"data_table_group":"runLog","name":"unitTransportCost","full_name":"","description":"","data_type":"bigint","table_order":12},{"id":13,"data_table_group":"runLog","name":"neighborhoodSize","full_name":"","description":"","data_type":"bigint","table_order":13},{"id":14,"data_table_group":"runLog","name":"budget","full_name":"","description":"","data_type":"bigint","table_order":14},{"id":15,"data_table_group":"runLog","name":"sdbudget","full_name":"","description":"","data_type":"bigint","table_order":15},{"id":16,"data_table_group":"runLog","name":"search","full_name":"","description":"","data_type":"bigint","table_order":16},{"id":17,"data_table_group":"runLog","name":"bid","full_name":"","description":"","data_type":"bigint","table_order":17},{"id":18,"data_table_group":"runLog","name":"agr","full_name":"","description":"","data_type":"bigint","table_order":18},{"id":19,"data_table_group":"runLog","name":"util","full_name":"","description":"","data_type":"decimal","table_order":19},{"id":20,"data_table_group":"runLog","name":"sdp","full_name":"","description":"","data_type":"decimal","table_order":20},{"id":21,"data_table_group":"runLog","name":"range","full_name":"","description":"","data_type":"decimal","table_order":21},{"id":22,"data_table_group":"runLog","name":"steps","full_name":"","description":"","data_type":"bigint","table_order":22},{"id":23,"data_table_group":"runLog","name":"luFile","full_name":"","description":"","data_type":"text","table_order":23},{"id":24,"data_table_group":"runLog","name":"tpFile","full_name":"","description":"","data_type":"text","table_order":24},{"id":25,"data_table_group":"runLog","name":"lufile2","full_name":"","description":"","data_type":"text","table_order":25},{"id":26,"data_table_group":"runLog","name":"tpFile2","full_name":"","description":"","data_type":"text","table_order":26},{"id":27,"data_table_group":"runLog","name":"agents","full_name":"","description":"","data_type":"text","table_order":27}],"number_of_files":1,"number_of_columns":27}"""


main = App.beginnerProgram { update = update, view = view, model = init }
