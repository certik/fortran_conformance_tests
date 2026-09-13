! rule: S10.2.1.3-023
! covers: c-ptr-component c-funptr-component team-type-component
! evidence: context-only
! requires: coarray
! images: 2
! F2023 10.2.1.3 p14 and C915: copy a wrapper, never a direct coindexed opaque designator.
! Only the ordinary payload is inspected after the cross-image copy.
module s10_2_1_3_023_cross_m
    use iso_c_binding, only: c_int
    implicit none
contains
    integer(c_int) function add_one(x) bind(c)
        integer(c_int), value :: x
        add_one = x + 1
    end function
end module
program s10_2_1_3_023_cross_image
    use iso_c_binding, only: c_int, c_ptr, c_funptr, c_loc, c_funloc
    use iso_fortran_env, only: team_type
    use s10_2_1_3_023_cross_m
    implicit none
    type :: envelope
        type(c_ptr) :: address
        type(c_funptr) :: procedure_address
        type(team_type) :: team
        integer :: payload
    end type
    type(envelope), save :: source[*]
    type(envelope) :: copy
    type(team_type) :: team
    integer(c_int), target :: value
    integer :: other
    if (num_images() < 2) error stop 'requires-two-images'
    value = this_image()
    source%address = c_loc(value)
    source%procedure_address = c_funloc(add_one)
    form team (1, team)
    source%team = team
    source%payload = 17 * this_image()
    other = mod(this_image(), num_images()) + 1
    sync all
    copy = source[other]
    if (copy%payload /= 17 * other) error stop 'ordinary-cross-image-payload'
    sync all
end program
