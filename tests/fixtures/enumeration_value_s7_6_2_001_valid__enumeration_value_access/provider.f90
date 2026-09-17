module enumeration_provider
implicit none
private
enumeration type, public :: public_kind
enumerator :: zebra_default, apple_default
end enumeration type public_kind
enumeration type, public :: confirmed_kind
enumerator :: zebra_confirmed, apple_visible, mango_private
end enumeration type confirmed_kind
enumeration type, private :: hidden_kind
enumerator :: hidden_zebra, exposed_apple, hidden_mango
end enumeration type hidden_kind
public :: zebra_confirmed
private :: mango_private
public :: exposed_apple
end module enumeration_provider
