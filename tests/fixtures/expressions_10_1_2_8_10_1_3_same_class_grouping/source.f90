module expr_precedence_mod
  implicit none
  type :: box
    integer :: value
  end type box
  interface operator(//)
    module procedure concat_box_box, concat_box_logical
  end interface
  interface operator(==)
    module procedure equal_box_box
  end interface
  interface operator(+)
    module procedure plus_box_box
  end interface
  interface operator(*)
    module procedure times_box_box
  end interface
  interface operator(**)
    module procedure power_box_box
  end interface
  interface operator(.neg.)
    module procedure neg_box
  end interface
  interface operator(.or.)
    module procedure or_box_box
  end interface
  interface operator(.join.)
    module procedure join_i
  end interface
  interface operator(.starstar.)
    module procedure starstar_i
  end interface
contains
  pure function concat_box_box(lhs, rhs) result(out)
    type(box), intent(in) :: lhs, rhs
    type(box) :: out
    out%value = 10*lhs%value + rhs%value
  end function concat_box_box
  pure logical function concat_box_logical(lhs, rhs)
    type(box), intent(in) :: lhs
    logical, intent(in) :: rhs
    concat_box_logical = rhs
  end function concat_box_logical
  pure logical function equal_box_box(lhs, rhs)
    type(box), intent(in) :: lhs, rhs
    equal_box_box = lhs%value == rhs%value
  end function equal_box_box
  pure function plus_box_box(lhs, rhs) result(out)
    type(box), intent(in) :: lhs, rhs
    type(box) :: out
    out%value = 100*lhs%value + rhs%value
  end function plus_box_box
  pure function times_box_box(lhs, rhs) result(out)
    type(box), intent(in) :: lhs, rhs
    type(box) :: out
    out%value = 10*lhs%value + rhs%value
  end function times_box_box
  pure function power_box_box(lhs, rhs) result(out)
    type(box), intent(in) :: lhs, rhs
    type(box) :: out
    out%value = 10*lhs%value + rhs%value
  end function power_box_box
  pure function neg_box(arg) result(out)
    type(box), intent(in) :: arg
    type(box) :: out
    out%value = 100 + arg%value
  end function neg_box
  pure function or_box_box(lhs, rhs) result(out)
    type(box), intent(in) :: lhs, rhs
    type(box) :: out
    out%value = 10*lhs%value + rhs%value
  end function or_box_box
  pure integer function join_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    join_i = 10*lhs + rhs
  end function join_i
  pure integer function starstar_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    starstar_i = 10*lhs + rhs
  end function starstar_i
end module expr_precedence_mod

program expr_operator_precedence
  use expr_precedence_mod
  implicit none
  integer :: checks, x
  logical :: ok
  type(box) :: a, b, c, r
  checks = 0
  x = -2**2
  if (x /= -4) error stop 'PREC:power-before-unary-minus'
  checks = checks + 1
  x = 2+3*4
  if (x /= 14) error stop 'PREC:multiply-before-plus'
  checks = checks + 1
  x = -3 + 10
  if (x /= 7) error stop 'PREC:unary-before-binary-plus'
  checks = checks + 1
  a = box(1); b = box(2); c = box(12)
  ok = a // b == c
  if (.not. ok) error stop 'PREC:character-before-relational'
  checks = checks + 1
  ok = .false. .or. 2+3 >= 5
  if (.not. ok) error stop 'PREC:relational-before-or'
  checks = checks + 1
  ok = .not. .false. .and. .false.
  if (ok) error stop 'PREC:not-before-and'
  checks = checks + 1
  ok = .true. .or. .false. .and. .false.
  if (.not. ok) error stop 'PREC:and-before-or'
  checks = checks + 1
  ok = .true. .or. .false. .eqv. .false.
  if (ok) error stop 'PREC:or-before-eqv'
  checks = checks + 1
  x = 1 + 2 .join. 3
  if (x /= 33) error stop 'PREC:defined-binary-lowest'
  checks = checks + 1
  x = (2+3)*4
  if (x /= 20) error stop 'PREC:parentheses-category'
  checks = checks + 1
  a = box(1); b = box(2); c = box(3)
  r = a + b ** c
  if (r%value /= 123) error stop 'P2:extended-intrinsic-precedence'
  checks = checks + 1
  r = .neg. a * b
  if (r%value /= 1012) error stop 'P2:defined-unary-highest'
  checks = checks + 1
  x = 4 + 5 .join. 6
  if (x /= 96) error stop 'P2:defined-binary-lowest'
  checks = checks + 1
  x = 2 * 3 .starstar. 4
  if (x /= 64) error stop 'P2:dotted-name-lowest'
  checks = checks + 1
  x = 10-3-2
  if (x /= 5) error stop 'P3:left-subtraction'
  checks = checks + 1
  x = 64/4/2
  if (x /= 8) error stop 'P3:left-division'
  checks = checks + 1
  x = 2**3**2
  if (x /= 512) error stop 'P3:right-exponentiation'
  checks = checks + 1
  a = box(4); b = box(5); c = box(6)
  r = a // b // c
  if (r%value /= 456) error stop 'P3:left-concat-boundary'
  checks = checks + 1
  a = box(1); b = box(2); c = box(3)
  r = a .or. b .or. c
  if (r%value /= 123) error stop 'P3:logical-same-class'
  checks = checks + 1
  x = 10-(3-2)
  if (x /= 9) error stop 'P3:parentheses-same-class'
  checks = checks + 1
  if (checks /= 20) error stop 'PREC:checks'
  write(*,'(a)') 'EXPRESSIONS PRECEDENCE OK'
end program expr_operator_precedence
