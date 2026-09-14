! rule: C705
! covers: extensible
! evidence: positive-control
program c705_bind_c
    use iso_c_binding, only: c_int
    implicit none
    type :: record
        integer(c_int) :: code
    end type
    class(record), pointer :: value => null()
    if (associated(value)) error stop 'association'
end program
