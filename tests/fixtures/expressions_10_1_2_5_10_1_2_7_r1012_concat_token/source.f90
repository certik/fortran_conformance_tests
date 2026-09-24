module expr_l3_defined_concat_mod
  implicit none
  type :: token
    integer :: value
  end type token
  interface operator(//)
    module procedure join_token
  end interface
  interface operator(.cat.)
    module procedure cat_char
  end interface
contains
  pure function join_token(lhs, rhs) result(out)
    type(token), intent(in) :: lhs, rhs
    type(token) :: out
    out%value = 10*lhs%value + rhs%value
  end function join_token
  pure function cat_char(lhs, rhs) result(out)
    character(len=*), intent(in) :: lhs, rhs
    character(len=len(lhs)+len(rhs)) :: out
    out = rhs // lhs
  end function cat_char
end module expr_l3_defined_concat_mod

program expr_l3_concat_layers
  use expr_l3_defined_concat_mod
  implicit none
  integer :: checks
  character(len=5) :: single_s, single_r
  character(len=4) :: joined_s, joined_r, joined_token
  type(token) :: a, b, c, d, e, f, left_one, left_two
  checks = 0
  single_s = 'x'
  if (len('x') /= 1) error stop 'L3:s-single-len'
  if (single_s /= 'x') error stop 'L3:s-single-value'
  checks = checks + 1
  joined_s = 'ab'//'cd'
  if (len('ab'//'cd') /= 4) error stop 'L3:s-concat-len'
  if (joined_s /= 'abcd') error stop 'L3:s-concat-value'
  checks = checks + 1
  a = token(1); b = token(2); c = token(3)
  left_one = a // b // c
  if (left_one%value /= 123) error stop 'L3:left-one'
  checks = checks + 1
  single_r = 'y'
  if (len('y') /= 1) error stop 'L3:r-single-len'
  if (single_r /= 'y') error stop 'L3:r-single-value'
  checks = checks + 1
  joined_r = 'pq'//'rs'
  if (len('pq'//'rs') /= 4) error stop 'L3:r-concat-len'
  if (joined_r /= 'pqrs') error stop 'L3:r-concat-value'
  checks = checks + 1
  d = token(4); e = token(5); f = token(6)
  left_two = d // e // f
  if (left_two%value /= 456) error stop 'L3:left-two'
  checks = checks + 1
  joined_token = 'lm'//'no'
  if (len('lm'//'no') /= 4) error stop 'L3:token-concat-len'
  if (joined_token /= 'lmno') error stop 'L3:token-concat-value'
  checks = checks + 1
  if (checks /= 7) error stop 'L3:checks'
  write(*,'(a)') 'EXPRESSIONS LEVEL 3 CONCAT OK'
end program expr_l3_concat_layers
