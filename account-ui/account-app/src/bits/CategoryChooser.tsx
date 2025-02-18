import React, {useContext, useEffect, useState} from "react";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
//  import { paths } from "../types/aaa-api.ts";
import { paths as adminApi } from "../types/admin-api";
import {RuntimeContext} from "../RuntimeContext";
import arxivCategories from "./arxivCategories"

export type CategoryType = adminApi["/v1/categories/{id}"]["get"]["responses"]["200"]["content"]["application/json"];


type CategoryGroupType = {
    group: string;
    subcategories: CategoryType[];
};

interface CategoryChooserProps {
    onSelect?: (category: CategoryType | null) => void;
}


const CategoryChooser: React.FC<CategoryChooserProps> = ({onSelect}) => {
    const runtimeContext = useContext(RuntimeContext);
    const [selectedCategory, setSelectedCategory] = useState<CategoryType | null>(null);
    const [categoryList, setCategoryList] = useState<CategoryType[]>(arxivCategories);
    const [categories, setCategories] = useState<CategoryGroupType[]>([]);

    useEffect(() => {
        fetch(runtimeContext.UP_API_URL +  "/categories/")
            .then(response => response.json())
            .then(data => setCategoryList(data))
            .catch(error => console.log(error));
    }, []);

    useEffect(() => {
        const categoryGroups: CategoryGroupType[] = Object.values(
            categoryList.reduce<Record<string, CategoryGroupType>>((acc, category) => {
                if (!acc[category.archive]) {
                    acc[category.archive] = { group: category.archive, subcategories: [] };
                }
                acc[category.archive].subcategories.push(category);
                return acc;
            }, {})
        );
        setCategories(categoryGroups);
    }, [categoryList]);

    const categoryOptions = categories
        .flatMap((categoryGroup) => [
            { group: categoryGroup.group, label: categoryGroup.group.toUpperCase(), isHeader: true } as const, // Header
            ...categoryGroup.subcategories.map((category) => ({
                group: categoryGroup.group,
                label: `${categoryGroup.group}.${category.subject_class} - ${category.category_name ?? "Unknown Category"}`, // ✅ Fallback for null values
                value: category, // Store full `CategoryType` object
                isHeader: false,
            })),
        ])
        .sort((a, b) => a.group.localeCompare(b.group));

    const selectedOption = categoryOptions.find(
        (option) => !option.isHeader && option.value.id === selectedCategory?.id
    ) ?? null;

    const setSelection = (selected: CategoryType | null) => {
        setSelectedCategory(selected);
        if (onSelect) {
            onSelect(selected);
        }
    }

    return (
        <Autocomplete
            options={categoryOptions.filter((cat) => !cat.isHeader)}
            groupBy={(option) => (!option.isHeader ? option.group.toUpperCase() : "")}
            getOptionLabel={(option) => option.label ?? "Unknown Category"}
            isOptionEqualToValue={(option, value) => !option.isHeader && !value.isHeader && option.value && value.value && option.value.id === value.value.id}
            renderInput={(params) => <TextField {...params} label="Your default category *" />}
            renderOption={(props, option) => (
                <li
                    {...props}
                    key={option.isHeader ? `header-${option.group}` : option.value.id}
                    style={{
                        fontWeight: option.isHeader ? "bold" : "normal",
                        paddingLeft: option.isHeader ? 0 : 16,
                    }}
                >
                    {option.label}
                </li>
            )}
            disableCloseOnSelect
            value={selectedOption} // ✅ Now correctly displays selected value
            onChange={(_event, newValue) =>
                setSelection(newValue && !newValue.isHeader ? newValue.value : null)
            }
        />
    );
};

export default CategoryChooser;
