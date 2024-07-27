---
title: Theming
slug: /develop/concepts/configuration/theming
---

# Theming

In this guide, we provide examples of how Streamlit page elements are affected
by the various theme config options. For a more high-level overview of
Streamlit themes, see the Themes section of the
[main concepts documentation](/get-started/fundamentals/additional-features#themes).

Streamlit themes are defined using regular config options: a theme can be set
via command line flag when starting your app using `streamlit run` or by
defining it in the `[theme]` section of a `.streamlit/config.toml` file. For
more information on setting config options, please refer to the
[Streamlit configuration documentation](/develop/concepts/configuration).

The following config options show the default Streamlit Light theme recreated
in the `[theme]` section of a `.streamlit/config.toml` file.

```toml
[theme]
primaryColor="#FF4B4B"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F0F2F6"
textColor="#31333F"
font="sans serif"
```

Let's go through each of these options, providing screenshots to demonstrate
what parts of a Streamlit app they affect where needed.

## primaryColor

`primaryColor` defines the accent color most often used throughout a Streamlit
app. A few examples of Streamlit widgets that use `primaryColor` include
`st.checkbox`, `st.slider`, and `st.text_input` (when focused).

![Primary Color](/images/theme_config_options/primaryColor.png)

<Tip>

Any CSS color can be used as the value for primaryColor and the other color
options below. This means that theme colors can be specified in hex or with
browser-supported color names like "green", "yellow", and
"chartreuse". They can even be defined in the RGB and HSL formats!

</Tip>

## backgroundColor

Defines the background color used in the main content area of your app.

## secondaryBackgroundColor

This color is used where a second background color is needed for added
contrast. Most notably, it is the sidebar's background color. It is also used
as the background color for most interactive widgets.

![Secondary Background Color](/images/theme_config_options/secondaryBackgroundColor.png)

## textColor

This option controls the text color for most of your Streamlit app.

## font

Selects the font used in your Streamlit app. Valid values are `"sans serif"`,
`"serif"`, and `"monospace"`. This option defaults to `"sans serif"` if unset
or invalid.

Note that code blocks are always rendered using the monospace font regardless of
the font selected here.

## base

An easy way to define custom themes that make small changes to one of the
preset Streamlit themes is to use the `base` option. Using `base`, the
Streamlit Light theme can be recreated as a custom theme by writing the
following:

```toml
[theme]
base="light"
```

The `base` option allows you to specify a preset Streamlit theme that your
custom theme inherits from. Any theme config options not defined in your theme
settings have their values set to those of the base theme. Valid values for
`base` are `"light"` and `"dark"`.

For example, the following theme config defines a custom theme nearly identical
to the Streamlit Dark theme, but with a new `primaryColor`.

```toml
[theme]
base="dark"
primaryColor="purple"
```

If `base` itself is omitted, it defaults to `"light"`, so you can define a
custom theme that changes the font of the Streamlit Light theme to serif with
the following config

```toml
[theme]
font="serif"
```

---
title: st.sidebar
slug: /develop/api-reference/layout/st.sidebar
description: st.sidebar displays items in a sidebar.
---

## st.sidebar

## Add widgets to sidebar

Not only can you add interactivity to your app with widgets, you can organize them into a sidebar. Elements can be passed to `st.sidebar` using object notation and `with` notation.

The following two snippets are equivalent:

```python
# Object notation
st.sidebar.[element_name]
```

```python
# "with" notation
with st.sidebar:
    st.[element_name]
```

Each element that's passed to `st.sidebar` is pinned to the left, allowing users to focus on the content in your app.

<Tip>

The sidebar is resizable! Drag and drop the right border of the sidebar to resize it! ↔️

</Tip>

Here's an example of how you'd add a selectbox and a radio button to your sidebar:

```python
import streamlit as st

# Using object notation
add_selectbox = st.sidebar.selectbox(
    "How would you like to be contacted?",
    ("Email", "Home phone", "Mobile phone")
)

# Using "with" notation
with st.sidebar:
    add_radio = st.radio(
        "Choose a shipping method",
        ("Standard (5-15 days)", "Express (2-5 days)")
    )
```

<Important>

The only elements that aren't supported using object notation are `st.echo`, `st.spinner`, and `st.toast`. To use these elements, you must use `with` notation.

</Important>

Here's an example of how you'd add [`st.echo`](/develop/api-reference/text/st.echo) and [`st.spinner`](/develop/api-reference/status/st.spinner) to your sidebar:

```python
import streamlit as st
import time

with st.sidebar:
    with st.echo():
        st.write("This code will be printed to the sidebar.")

    with st.spinner("Loading..."):
        time.sleep(5)
    st.success("Done!")
```
