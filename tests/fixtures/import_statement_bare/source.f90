program import_statement_bare_effect
  implicit none
  integer :: hx, hz, observed
  hx = 5
  hz = 100
  observed = -77
  call inner(observed)
  if (observed /= 11) error stop 1
  if (hz /= 6) error stop 2
  write(*,'(a)') 'IMPORT STATEMENT BARE OK'
contains
  subroutine inner(out)
    import
    integer, intent(out) :: out
    hz = 6
    out = hx + hz
  end subroutine
end program import_statement_bare_effect
