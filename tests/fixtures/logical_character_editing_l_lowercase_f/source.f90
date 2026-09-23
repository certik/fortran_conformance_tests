program lce_l_lowercase_f
  implicit none
! rule: S13.7.3-003
! covers: lowercase-f-false
  integer :: checks
  character(len=2) :: field
  character(len=1) :: boundary_field
  character(len=3) :: record
  logical :: value, boundary_value
  integer :: guard, boundary_guard, ios
  checks = 0
  field = '.f'
  boundary_field = 't'
  record = field // boundary_field
  guard = 0
  boundary_guard = 0
  call mark_logical('lower-f', value, guard, .true.)
  call expect_pre_logical(value, .true., guard, 'lower-f')
  call mark_logical('lower-f-boundary', boundary_value, boundary_guard, .false.)
  call expect_pre_logical(boundary_value, .false., boundary_guard, 'lower-f-boundary')
  ios = -1
  read(record,'(L2,L1)', iostat=ios) value, boundary_value
  call expect_int(ios, 0, 'lower-f-ios')
  call expect_logical(value, .false., 'lower-f')
  call expect_logical(boundary_value, .true., 'lower-f-boundary')
  if (checks /= 5) then
    write(*,'(a)') 'LCE:l_lowercase_f:check-total'
    error stop 1
  end if
  write(*,'(a)') 'LOGICAL CHARACTER EDITING L LOWERCASE F OK'
contains
  subroutine mark_logical(name, value, guard, sentinel)
    character(len=*), intent(in) :: name
    logical, intent(out) :: value
    integer, intent(out) :: guard
    logical, intent(in) :: sentinel
    if (len(name) == 0) error stop 1
    value = sentinel
    guard = 1
  end subroutine mark_logical
  subroutine mark_text(name, value, guard, sentinel)
    character(len=*), intent(in) :: name
    character(len=*), intent(out) :: value
    integer, intent(out) :: guard
    character(len=*), intent(in) :: sentinel
    if (len(name) == 0) error stop 1
    value = sentinel
    guard = 1
  end subroutine mark_text
  subroutine expect_text(observed, expected, label)
    character(len=*), intent(in) :: observed, expected, label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'LCE:length', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'LCE:text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_text
  subroutine expect_logical(observed, expected, label)
    logical, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed .neqv. expected) then
      write(*,'(a,1x,a)') 'LCE:logical', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_logical
  subroutine expect_int(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'LCE:int', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_int
  subroutine expect_pre_logical(observed, expected, guard, label)
    logical, intent(in) :: observed, expected
    integer, intent(in) :: guard
    character(len=*), intent(in) :: label
    if (guard /= 1) then
      write(*,'(a,1x,a)') 'LCE:pre-logical', label
      error stop 1
    end if
    if (observed .neqv. expected) then
      write(*,'(a,1x,a)') 'LCE:pre-logical', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_pre_logical
  subroutine expect_pre_text(observed, expected, guard, label)
    character(len=*), intent(in) :: observed, expected, label
    integer, intent(in) :: guard
    if (guard /= 1) then
      write(*,'(a,1x,a)') 'LCE:pre-text', label
      error stop 1
    end if
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'LCE:pre-text', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'LCE:pre-text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_pre_text
end program lce_l_lowercase_f
