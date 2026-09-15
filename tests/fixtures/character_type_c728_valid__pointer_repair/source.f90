function f() result(value)
    implicit none
    character(3), pointer :: value
    character(3), target, save :: target = 'ABC'
    value => target
end function
