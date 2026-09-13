! rule: S10.2.1.3-003
! covers: scalar-target array-target strided-target association-preserved
! F2023 10.2.1.3 p2.
program s10_2_1_3_003_valid
    implicit none
    integer, target :: scalar, a(6)
    integer, pointer :: p, q(:)
    scalar = 5
    p => scalar
    p = 17
    if (.not. associated(p, scalar)) error stop 'scalar-association'
    if (scalar /= 17) error stop 'scalar-target'
    a = -1
    q => a
    q = [2, 3, 5, 7, 11, 13]
    if (.not. associated(q, a)) error stop 'array-association'
    if (any(a /= [2, 3, 5, 7, 11, 13])) error stop 'array-target'
    q => a(2:6:2)
    q = [17, 19, 23]
    if (.not. associated(q, a(2:6:2))) error stop 'strided-association'
    if (any(a /= [2, 17, 5, 19, 11, 23])) error stop 'strided-target'
    q = -3
    if (any(a /= [2, -3, 5, -3, 11, -3])) error stop 'strided-expansion'
end program
