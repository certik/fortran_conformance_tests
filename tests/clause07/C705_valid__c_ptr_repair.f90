! rule: C705
! covers: nonclass-intrinsic-module-types
! evidence: positive-control
program c705_c_ptr
    use iso_c_binding, only: c_ptr
    implicit none
    type(c_ptr), pointer :: value => null()
    if (associated(value)) error stop 'association'
end program
