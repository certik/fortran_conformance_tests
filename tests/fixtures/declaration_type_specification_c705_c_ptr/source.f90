program c705_c_ptr
    use iso_c_binding, only: c_ptr
    implicit none
    class(c_ptr), pointer :: value => null()
    if (associated(value)) error stop 'association'
end program
