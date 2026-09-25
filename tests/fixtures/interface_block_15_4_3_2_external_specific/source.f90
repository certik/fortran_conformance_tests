program interface_block_external_specific
  implicit none
  integer :: f_value, sub_value, sum_value
  ! rule: S15.4.3.1-001 S15.4.3.2-009
  ! covers: function/subroutine/specification statements in a specific interface body for externals
  interface
    integer function ib_func()
    end function ib_func
    subroutine ib_sub(x)
      integer, intent(out) :: x
    end subroutine ib_sub
    integer function ib_sum(values)
      integer, intent(in) :: values(:)
    end function ib_sum
    integer function ib_body()
    end function ib_body
    integer function ib_both()
    end function ib_both
  end interface
  f_value = -100
  f_value = ib_func()
  if (f_value /= 42) error stop 1
  sub_value = -101
  call ib_sub(sub_value)
  if (sub_value /= 24) error stop 2
  sum_value = -102
  sum_value = ib_sum([5, 37])
  if (sum_value /= 42) error stop 3
  f_value = -103
  f_value = ib_body()
  if (f_value /= 52) error stop 4
  f_value = -104
  f_value = ib_both()
  if (f_value /= 62) error stop 5
  print '(a)', 'INTERFACE BLOCK EXTERNAL SPECIFIC OK'
end program interface_block_external_specific

integer function ib_func()
  implicit none
  ib_func = 42
end function ib_func

integer function ib_func_alt()
  implicit none
  ib_func_alt = 41
end function ib_func_alt

subroutine ib_sub(x)
  implicit none
  integer, intent(out) :: x
  x = 24
end subroutine ib_sub

subroutine ib_sub_alt(x)
  implicit none
  integer, intent(out) :: x
  x = 23
end subroutine ib_sub_alt

integer function ib_sum(values)
  implicit none
  integer, intent(in) :: values(:)
  ib_sum = sum(values)
end function ib_sum

integer function ib_sum_alt(values)
  implicit none
  integer, intent(in) :: values(:)
  ib_sum_alt = sum(values) - 1
end function ib_sum_alt

integer function ib_body()
  implicit none
  ib_body = 52
end function ib_body

integer function ib_body_alt()
  implicit none
  ib_body_alt = 51
end function ib_body_alt

integer function ib_both()
  implicit none
  ib_both = 62
end function ib_both

integer function ib_both_alt()
  implicit none
  ib_both_alt = 61
end function ib_both_alt
