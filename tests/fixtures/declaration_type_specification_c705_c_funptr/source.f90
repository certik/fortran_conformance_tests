program c705_c_funptr
    use iso_c_binding, only: c_funptr
    implicit none
    class(c_funptr), pointer :: value => null()
    if (associated(value)) error stop 'association'
end program
