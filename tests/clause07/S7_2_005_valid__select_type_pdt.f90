! rule: S7.2-005
! covers: select-type-pdt
! evidence: effect
program type_parameters_assumed_selector_pdt
    implicit none
    ! These PDT discriminators are not intrinsic representation selectors.
    integer, parameter :: family = 1, other_family = 2
    type :: packet(k, n)
        integer, kind :: k
        integer, len :: n
        integer :: payload(n)
    end type packet
    type(packet(family, 2)) :: short
    type(packet(family, 5)) :: long
    type(packet(other_family, 2)) :: other

    if (short%k /= family) error stop 1
    if (short%n /= 2) error stop 2
    if (size(short%payload) /= 2) error stop 3
    if (lbound(short%payload, 1) /= 1) error stop 4
    short%payload(:) = [7, 11]
    if (long%k /= family) error stop 5
    if (long%n /= 5) error stop 6
    if (size(long%payload) /= 5) error stop 7
    if (lbound(long%payload, 1) /= 1) error stop 8
    long%payload(:) = [17, 19, 23, 29, 31]
    if (other%k /= other_family) error stop 9
    if (other%n /= 2) error stop 10
    if (size(other%payload) /= 2) error stop 11
    if (lbound(other%payload, 1) /= 1) error stop 12
    other%payload(:) = [37, 41]

    if (classify(short, 2, [7, 11]) /= 101) error stop 13
    if (classify(long, 5, [17, 19, 23, 29, 31]) /= 101) error stop 14
    if (classify(other, 2, [37, 41]) /= 202) error stop 15
contains
    integer function classify(value, expected_n, expected_payload) result(tag)
        class(*), intent(in) :: value
        integer, intent(in) :: expected_n
        integer, intent(in) :: expected_payload(:)

        if (size(expected_payload) /= expected_n) error stop 16
        select type (item => value)
        type is (packet(family, *))
            if (item%k /= family) error stop 17
            if (kind(item%n) /= kind(0)) error stop 18
            if (item%n /= expected_n) error stop 19
            if (size(item%payload) /= expected_n) error stop 20
            if (lbound(item%payload, 1) /= 1) error stop 21
            if (any(item%payload /= expected_payload)) error stop 22
            tag = 101
        type is (packet(other_family, *))
            if (item%k /= other_family) error stop 23
            if (kind(item%n) /= kind(0)) error stop 24
            if (item%n /= expected_n) error stop 25
            if (size(item%payload) /= expected_n) error stop 26
            if (lbound(item%payload, 1) /= 1) error stop 27
            if (any(item%payload /= expected_payload)) error stop 28
            tag = 202
        class default
            error stop 29
        end select
    end function classify
end program type_parameters_assumed_selector_pdt
