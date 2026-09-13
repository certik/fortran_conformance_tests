! rule: S10.2.1.3-024
! covers: data-pointer array-pointer procedure-pointer disassociated-source
! F2023 10.2.1.3 p15: association copying is not target-value copying.
module s10_2_1_3_024_m
    implicit none
    abstract interface
        integer function transform(n)
            integer, intent(in) :: n
        end function
    end interface
    type :: packet
        integer, pointer :: scalar => null()
        integer, pointer :: values(:) => null()
        procedure(transform), pointer, nopass :: action => null()
    end type
contains
    integer function double_value(n)
        integer, intent(in) :: n
        double_value = 2 * n
    end function
end module
program s10_2_1_3_024_valid
    use s10_2_1_3_024_m
    implicit none
    type(packet) :: source, copy
    integer, target :: scalar, values(6)
    scalar = 17
    values = [2, 3, 5, 7, 11, 13]
    source%scalar => scalar
    source%values => values(2:6:2)
    source%action => double_value
    copy = source
    if (.not. associated(copy%scalar, scalar)) error stop 'data-pointer'
    if (.not. associated(copy%values, values(2:6:2))) error stop 'array-pointer'
    if (.not. associated(copy%action, double_value)) error stop 'procedure-pointer'
    if (copy%action(5) /= 10) error stop 'procedure-call'
    copy%scalar = 41
    copy%values(2) = 43
    if (scalar /= 41 .or. values(4) /= 43) error stop 'shared-live-targets'
    nullify(source%scalar, source%values, source%action)
    copy = source
    if (associated(copy%scalar)) error stop 'disassociated-data-pointer'
    if (associated(copy%values)) error stop 'disassociated-array-pointer'
    if (associated(copy%action)) error stop 'disassociated-procedure-pointer'
end program
