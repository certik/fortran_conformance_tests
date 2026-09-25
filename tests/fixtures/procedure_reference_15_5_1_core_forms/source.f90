module procedure_reference_15_5_1_core_m
  implicit none
  integer :: ping_seen = -91
  integer :: ping_empty_seen = -92
contains
  integer function f0()
    f0 = 11
  end function
  integer function f0_alt()
    f0_alt = 12
  end function
  integer function inc(n)
    integer, intent(in) :: n
    inc = n + 1
  end function
  subroutine ping
    ping_seen = 31
  end subroutine
  subroutine ping_other
    ping_seen = 131
  end subroutine
  subroutine ping_empty()
    ping_empty_seen = 32
  end subroutine
  subroutine ping_empty_other()
    ping_empty_seen = 132
  end subroutine
  subroutine set_value(x)
    integer, intent(out) :: x
    x = 23
  end subroutine
  subroutine set_value_other(x)
    integer, intent(out) :: x
    x = 24
  end subroutine
  subroutine take(a)
    integer, intent(out) :: a
    a = 6
  end subroutine
  subroutine take_other(a)
    integer, intent(out) :: a
    a = 16
  end subroutine
  subroutine mix(a, b, out)
    integer, intent(in) :: a, b
    integer, intent(out) :: out
    out = 100 * a + b
  end subroutine
  subroutine accept_in(a, seen)
    integer, intent(in) :: a
    integer, intent(out) :: seen
    seen = a
  end subroutine
  subroutine set_out(x)
    integer, intent(out) :: x
    x = 9
  end subroutine
  subroutine set_out_other(x)
    integer, intent(out) :: x
    x = 19
  end subroutine
end module procedure_reference_15_5_1_core_m

program procedure_reference_15_5_1_core
  use procedure_reference_15_5_1_core_m
  implicit none
  integer :: observed_empty, observed_actual, actual_value
  integer :: pos, kwout, expr_seen, var_seen, checks
  checks = 0
  observed_empty = -9
  observed_empty = f0()
  if (observed_empty /= 11) error stop 101
  checks = checks + 1
  observed_actual = -9
  observed_actual = inc(4)
  if (observed_actual /= 5) error stop 102
  checks = checks + 1
  ping_seen = -91
  call ping
  if (ping_seen /= 31) error stop 103
  checks = checks + 1
  ping_empty_seen = -92
  call ping_empty()
  if (ping_empty_seen /= 32) error stop 104
  checks = checks + 1
  actual_value = -1
  call set_value(actual_value)
  if (actual_value /= 23) error stop 105
  checks = checks + 1
  pos = -5
  call take(pos)
  if (pos /= 6) error stop 106
  checks = checks + 1
  kwout = -7
  call mix(b=2, a=5, out=kwout)
  if (kwout /= 502) error stop 107
  checks = checks + 1
  expr_seen = -8
  call accept_in(2 + 3, expr_seen)
  if (expr_seen /= 5) error stop 108
  checks = checks + 1
  var_seen = -9
  call set_out(var_seen)
  if (var_seen /= 9) error stop 109
  checks = checks + 1
  if (checks /= 9) error stop 199
  print '(a)', 'PROCEDURE REFERENCE CORE OK'
end program procedure_reference_15_5_1_core
