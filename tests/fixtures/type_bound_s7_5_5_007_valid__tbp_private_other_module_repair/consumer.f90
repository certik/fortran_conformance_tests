module tbp_consumer
use tbp_provider, only: object
implicit none
contains
integer function attempt() result(observed)
object%payload = 17
observed = object%secret()
end function attempt
end module tbp_consumer
