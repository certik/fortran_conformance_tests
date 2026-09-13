! rule: S10.2.1.3-026
! covers: intrinsic-component nested-derived-component array-component no-matching-type-bound-assignment
! F2023 10.2.1.3 p15-p16.
program s10_2_1_3_026_valid
    implicit none
    type :: inner
        integer :: n
        real :: x
    end type
    type :: packet
        integer :: tag
        character(3) :: text
        logical :: flag
        type(inner) :: scalar, values(2)
    end type
    type(packet) :: source, copy
    source%tag = 17
    source%text = 'abc'
    source%flag = .true.
    source%scalar%n = 23
    source%scalar%x = 1.5
    source%values(1)%n = 31
    source%values(1)%x = 2.5
    source%values(2)%n = 43
    source%values(2)%x = -3.5
    copy = source
    if (copy%tag /= 17 .or. copy%text /= 'abc' .or. .not. copy%flag) error stop 'intrinsic-components'
    if (copy%scalar%n /= 23 .or. copy%scalar%x /= 1.5) error stop 'nested-derived-component'
    if (copy%values(1)%n /= 31 .or. copy%values(1)%x /= 2.5) error stop 'array-first'
    if (copy%values(2)%n /= 43 .or. copy%values(2)%x /= -3.5) error stop 'array-second'
    copy%values(1)%n = -1
    if (source%values(1)%n /= 31) error stop 'independent-components'
end program
