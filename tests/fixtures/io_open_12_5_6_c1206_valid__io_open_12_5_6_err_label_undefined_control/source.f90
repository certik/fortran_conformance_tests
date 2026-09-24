program p
        integer :: u
        open(newunit=u, status='scratch', err=99)
        close(u, status='delete')
99      continue
        end program p
