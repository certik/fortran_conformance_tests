module tbp_provider
implicit none
contains
integer function provider_value() result(value)
value = 22
end function provider_value
end module tbp_provider
