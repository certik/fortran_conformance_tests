program integer_literal_bounded_inventory
    use iso_fortran_env, only: integer_kinds
    implicit none
    if (size(integer_kinds) < 1) error stop 1
    if (.not. any(integer_kinds == kind(0))) error stop 2
    if (selected_int_kind(18) < 0) error stop 3
    if (size(integer_kinds) > 16) stop 77
end program
