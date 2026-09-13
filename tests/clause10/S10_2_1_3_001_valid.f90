! rule: S10.2.1.3-001
! covers: same-type-value overlap-forward overlap-backward reversal lhs-index-from-old-value substring-overlap self-reallocation
! F2023 10.2.1.3 p1 and p4: snapshot effects, not an execution-order requirement.
program s10_2_1_3_001_valid
    implicit none
    integer :: a(5), b(3), scalar
    integer, allocatable :: values(:)
    character(5) :: text
    logical :: flag
    scalar = 17
    scalar = scalar + 3
    if (scalar /= 20) error stop 'same-type-value'
    flag = .true.
    flag = .not. flag
    if (flag) error stop 'logical-value'
    a = [2, 5, 9, 14, 20]
    a(2:5) = a(1:4)
    if (any(a /= [2, 2, 5, 9, 14])) error stop 'overlap-forward'
    a = [2, 5, 9, 14, 20]
    a(1:4) = a(2:5)
    if (any(a /= [5, 9, 14, 20, 20])) error stop 'overlap-backward'
    a = [2, 5, 9, 14, 20]
    a = a(5:1:-1)
    if (any(a /= [20, 14, 9, 5, 2])) error stop 'reversal'
    b = [2, 1, 9]
    b(b(1)) = b(3)
    if (any(b /= [2, 9, 9])) error stop 'lhs-index-from-old-value'
    text = 'abcde'
    text(2:5) = text(1:4)
    if (text /= 'aabcd') error stop 'substring-overlap'
    values = [2, 5, 9, 14, 20]
    values = values(2:4)
    if (.not. allocated(values)) error stop 'self-reallocation-status'
    if (size(values) /= 3) error stop 'self-reallocation-shape'
    if (any(values /= [5, 9, 14])) error stop 'self-reallocation-value'
end program
