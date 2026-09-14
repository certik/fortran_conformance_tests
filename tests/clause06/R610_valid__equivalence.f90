! rule: R610
! covers: equiv-op
! evidence: positive-control
module r610_equivalence_m
    implicit none
    type :: flag
        logical :: set
    end type flag
    interface operator (.eqv.)
        module procedure equivalent_flags
    end interface
    interface operator (.neqv.)
        module procedure nonequivalent_flags
    end interface
contains
    logical function equivalent_flags(left, right) result(value)
        type(flag), intent(in) :: left, right
        value = left%set .eqv. right%set
    end function equivalent_flags

    logical function nonequivalent_flags(left, right) result(value)
        type(flag), intent(in) :: left, right
        value = left%set .neqv. right%set
    end function nonequivalent_flags
end module r610_equivalence_m

program extended_equivalence
    use r610_equivalence_m
    implicit none
    logical, parameter :: left_values(4) = [.false., .false., .true., .true.]
    logical, parameter :: right_values(4) = [.false., .true., .false., .true.]
    integer, parameter :: equivalent(4) = [1, 0, 0, 1]
    integer, parameter :: nonequivalent(4) = [0, 1, 1, 0]
    type(flag) :: left, right
    integer :: i
    logical :: result

    do i = 1, 4
        left%set = left_values(i)
        right%set = right_values(i)
        result = left .eqv. right
        if (merge(1, 0, result) /= equivalent(i)) error stop 1
        result = left .neqv. right
        if (merge(1, 0, result) /= nonequivalent(i)) error stop 2
    end do
end program extended_equivalence
