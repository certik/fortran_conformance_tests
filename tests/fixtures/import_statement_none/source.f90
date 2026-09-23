program import_statement_none_effect
  implicit none
  integer :: hz, observed
  hz = 100
  observed = -77
  call inner(observed)
  if (observed /= 7) error stop 1
  if (hz /= 100) error stop 2
  write(*,'(a)') 'IMPORT STATEMENT NONE OK'
contains
  subroutine inner(out)
    import, none
    integer, intent(out) :: out
    integer :: hz
    hz = 7
    out = hz
  end subroutine
end program import_statement_none_effect
