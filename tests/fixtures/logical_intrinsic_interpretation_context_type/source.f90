program lio_context_type
  implicit none
  integer :: checks
  checks=17
  if (.false. .or. .true.) then
    checks=checks+1
  else
    write(*,'(a)') 'LIO:context_type:if-context-or'
    error stop
  end if
  call require_false(.true. .eqv. .false., 'LIO:context_type:logical-dummy-eqv')
  call require_true(.not. .false., 'LIO:context_type:logical-dummy-not')
  if (checks /= 20) then
    write(*,'(a)') 'LIO:context_type:check-total'
    error stop
  end if
  write(*,'(a)') 'LOGICAL INTRINSIC INTERPRETATION CONTEXT TYPE OK'
contains
  subroutine require_true(value, token)
    logical, intent(in) :: value
    character(len=*), intent(in) :: token
    if (value) then
      checks=checks+1
    else
      write(*,'(a)') token
      error stop
    end if
  end subroutine require_true
  subroutine require_false(value, token)
    logical, intent(in) :: value
    character(len=*), intent(in) :: token
    if (value) then
      write(*,'(a)') token
      error stop
    else
      checks=checks+1
    end if
  end subroutine require_false
end program lio_context_type
