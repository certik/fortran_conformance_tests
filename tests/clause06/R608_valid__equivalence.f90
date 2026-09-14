! rule: R608
! covers: equiv-op
! evidence: positive-control
program intrinsic_equivalence
    implicit none
    logical, parameter :: left(4) = [.false., .false., .true., .true.]
    logical, parameter :: right(4) = [.false., .true., .false., .true.]
    integer, parameter :: equivalent(4) = [1, 0, 0, 1]
    integer, parameter :: nonequivalent(4) = [0, 1, 1, 0]
    integer :: i
    logical :: result

    do i = 1, 4
        result = left(i) .eqv. right(i)
        if (merge(1, 0, result) /= equivalent(i)) error stop 1
        result = left(i) .neqv. right(i)
        if (merge(1, 0, result) /= nonequivalent(i)) error stop 2
    end do
end program intrinsic_equivalence
