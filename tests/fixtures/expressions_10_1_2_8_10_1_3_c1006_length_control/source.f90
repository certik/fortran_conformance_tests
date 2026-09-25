module expr_defined_binary_mod
  implicit none
  interface operator(.join.)
    module procedure join_i
  end interface
  interface operator(.b.)
    module procedure b_i
  end interface
  interface operator(.union.)
    module procedure union_i
  end interface
  interface operator(.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.)
    module procedure long_i
  end interface
contains
  pure integer function join_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    join_i = 10*lhs + rhs
  end function join_i
  pure integer function b_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    b_i = lhs + 10*rhs
  end function b_i
  pure integer function union_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    union_i = 100*lhs + rhs
  end function union_i
  pure integer function long_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    long_i = 1000*lhs + rhs
  end function long_i
end module expr_defined_binary_mod

program expr_defined_binary_forms
  use expr_defined_binary_mod
  implicit none
  integer :: checks, x
  logical :: ok
  checks = 0
  ok = .true. .and. .true.
  if (.not. ok) error stop 'GEN:level5-base'
  checks = checks + 1
  x = 1 + 2 .join. 3 * 4
  if (x /= 42) error stop 'GEN:defined-after-intrinsic'
  checks = checks + 1
  x = 1 .join. 2 .join. 3
  if (x /= 123) error stop 'GEN:defined-left-chain'
  checks = checks + 1
  x = 1 .join. (2 .join. 3)
  if (x /= 33) error stop 'GEN:parenthesized-defined-right'
  checks = checks + 1
  ok = .false. .or. .true.
  if (.not. ok) error stop 'R1023:single-level5'
  checks = checks + 1
  x = 4 .join. 5
  if (x /= 45) error stop 'R1023:defined-operation'
  checks = checks + 1
  x = 6 .join. 7 .join. 8
  if (x /= 678) error stop 'R1023:left-recursive-defined'
  checks = checks + 1
  x = 6 .join. (7 .join. 8)
  if (x /= 138) error stop 'R1023:right-parenthesized'
  checks = checks + 1
  x = 2 .b. 3
  if (x /= 32) error stop 'R1024:single-letter'
  checks = checks + 1
  x = 2 .union. 3
  if (x /= 203) error stop 'R1024:multiple-letters'
  checks = checks + 1
  x = 2 .aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. 3
  if (x /= 2003) error stop 'C1006:sixty-three'
  checks = checks + 1
  if (checks /= 11) error stop 'GEN:checks'
  write(*,'(a)') 'EXPRESSIONS DEFINED BINARY OK'
end program expr_defined_binary_forms
